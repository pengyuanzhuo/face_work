# -*- coding: utf-8 -*-
"""
Created on Mon Apr 24 15:43:29 2017

@author: zhaoy
"""
import numpy as np
import cv2

from matlab_cp2tform import get_similarity_transform_for_cv2

# reference facial points, a list of coordinates (x,y)
REFERENCE_FACIAL_POINTS = [
    [30.29459953,  51.69630051],
    [65.53179932,  51.50139999],
    [48.02519989,  71.73660278],
    [33.54930115,  92.3655014],
    [62.72990036,  92.20410156]
]

DEFAULT_CROP_SIZE = (96, 112)

class FaceWarpException(Exception):
    def __str__(self):
        return 'In File {}:{}'.format(
            __file__, super.__str__(self))


def get_reference_facial_points(output_size=None,
                                inner_padding_factor=0.0,
                                outer_padding=(0, 0),
                                default_square=False):
    """
    Function:
    ----------
        get reference 5 key points according to crop settings:

        0. Set default crop_size:
            if default_square: 
                crop_size = (112, 112)
            else: 
                crop_size = (96, 112)
        1. Pad the crop_size by inner_padding_factor in each side;
        2. Resize crop_size into (output_size - outer_padding*2),
            pad into output_size with outer_padding;
        3. Output reference_5point;

    Parameters:
    ----------
        @output_size: (w, h) or None
            size of aligned face image
        @inner_padding_factor: (w_factor, h_factor)
            padding factor for inner (w, h)
        @outer_padding: (w_pad, h_pad)
            each row is a pair of coordinates (x, y)
        @default_square: True or False
            if True:
                default crop_size = (112, 112)
            else:
                default crop_size = (96, 112);

        !!! make sure, if output_size is not None:
                (output_size - outer_padding) 
                = some_scale * (default crop_size * (1.0 + inner_padding_factor))
    Returns:
    ----------
        @reference_5point: 5x2 np.array
            each row is a pair of transformed coordinates (x, y)
    """
    print '\n===> get_reference_facial_points():'

    print '---> Params:'
    print '            output_size: ', output_size
    print '            inner_padding_factor: ', inner_padding_factor
    print '            outer_padding:', outer_padding
    print '            default_square: ', default_square

    tmp_5pts = np.array(REFERENCE_FACIAL_POINTS)
    tmp_crop_size = np.array(DEFAULT_CROP_SIZE)

    # 0) make the inner region a square
    if default_square:
        size_diff = max(tmp_crop_size) - tmp_crop_size
        tmp_5pts += size_diff / 2
        tmp_crop_size += size_diff

    print '---> default:'
    print '              crop_size = ', tmp_crop_size
    print '              reference_5pts = ', tmp_5pts

    if (output_size and
            output_size[0] == tmp_crop_size[0] and
            output_size[1] == tmp_crop_size[1]):
        print 'output_size == DEFAULT_CROP_SIZE {}: return default reference points'.format(tmp_crop_size)
        return tmp_5pts

    if (inner_padding_factor == 0 and
            outer_padding == (0, 0)):
        if output_size is None:
            print 'No paddings to do: return default reference points'
            return tmp_5pts
        else:
            raise FaceWarpException(
                'No paddings to do, output_size must be None or {}'.format(tmp_crop_size))

    # check output size
    if not (0 <= inner_padding_factor <= 1.0):
        raise FaceWarpException('Not (0 <= inner_padding_factor <= 1.0)')

    if ((inner_padding_factor > 0 or outer_padding[0] > 0 or outer_padding[1] > 0)
            and output_size is None):
        output_size = tmp_crop_size * \
            (1 + inner_padding_factor * 2).astype(np.int32)
        output_size += np.array(outer_padding)
        print '              deduced from paddings, output_size = ', output_size

    if not (outer_padding[0] < output_size[0]
            and outer_padding[1] < output_size[1]):
        raise FaceWarpException('Not (outer_padding[0] < output_size[0]'
                                'and outer_padding[1] < output_size[1])')

    # 1) pad the inner region according inner_padding_factor
    print '---> STEP1: pad the inner region according inner_padding_factor'
    if inner_padding_factor > 0:
        size_diff = tmp_crop_size * inner_padding_factor * 2
        tmp_5pts += size_diff / 2
        tmp_crop_size += np.round(size_diff).astype(np.int32)

    print '              crop_size = ', tmp_crop_size
    print '              reference_5pts = ', tmp_5pts

    # 2) resize the padded inner region
    print '---> STEP2: resize the padded inner region'
    size_bf_outer_pad = np.array(output_size) - np.array(outer_padding) * 2
    print '              crop_size = ', tmp_crop_size
    print '              size_bf_outer_pad = ', size_bf_outer_pad

    if size_bf_outer_pad[0] * tmp_crop_size[1] != size_bf_outer_pad[1] * tmp_crop_size[0]:
        raise FaceWarpException('Must have (output_size - outer_padding)'
                                '= some_scale * (crop_size * (1.0 + inner_padding_factor)')

    scale_factor = size_bf_outer_pad[0].astype(np.float32) / tmp_crop_size[0]
    print '              resize scale_factor = ', scale_factor
    tmp_5pts = tmp_5pts * scale_factor
    tmp_crop_size = size_bf_outer_pad
    print '              crop_size = ', tmp_crop_size
    print '              reference_5pts = ', tmp_5pts

    # 3) add outer_padding to make output_size
    reference_5point = tmp_5pts + np.array(outer_padding)
    tmp_crop_size = output_size
    print '---> STEP3: add outer_padding to make output_size'
    print '              crop_size = ', tmp_crop_size
    print '              reference_5pts = ', tmp_5pts

    print '===> end get_reference_facial_points\n'

    return reference_5point


def get_affine_transform_matrix(src_pts, dst_pts):
    """
    Function:
    ----------
        get affine transform matrix 'tfm' from src_pts to dst_pts

    Parameters:
    ----------
        @src_pts: Kx2 np.array
            source points matrix, each row is a pair of coordinates (x, y)

        @dst_pts: Kx2 np.array
            destination points matrix, each row is a pair of coordinates (x, y)

    Returns:
    ----------
        @tfm: 2x3 np.array
            transform matrix from src_pts to dst_pts
    """

    tfm = np.float32([[1, 0, 0], [0, 1, 0]])
    n_pts = src_pts.shape[0]
    ones = np.ones((n_pts, 1), src_pts.dtype)
    src_pts_ = np.hstack([src_pts, ones])
    dst_pts_ = np.hstack([dst_pts, ones])

    A, res, rank, s = np.linalg.lstsq(src_pts_, dst_pts_)

    if rank == 3:
        tfm = np.float32([
            [A[0, 0], A[1, 0], A[2, 0]],
            [A[0, 1], A[1, 1], A[2, 1]]
        ])
    elif rank == 2:
        tfm = np.float32([
            [A[0, 0], A[1, 0], 0],
            [A[0, 1], A[1, 1], 0]
        ])

    return tfm


def warp_and_crop_face(src_img,
                       facial_pts,
                       reference_pts=None,
                       crop_size=(96, 112),
                       align_type='smilarity'):
    """
    Function:
    ----------
        apply affine transform 'trans' to uv

    Parameters:
    ----------
        @src_img: 3x3 np.array
            input image
        @facial_pts: could be
            1)a list of K coordinates (x,y)
        or
            2) Kx2 or 2xK np.array
            each row or col is a pair of coordinates (x, y)
        @reference_pts: could be
            1) a list of K coordinates (x,y)
        or
            2) Kx2 or 2xK np.array
            each row or col is a pair of coordinates (x, y)
        or
            3) None
            if None, use default reference facial points
        @crop_size: (w, h)
            output face image size
        @align_type: transform type, could be one of
            1) 'similarity': use similarity transform
            2) 'cv2_affine': use the first 3 points to do affine transform,
                    by calling cv2.getAffineTransform()
            3) 'affine': use all points to do affine transform

    Returns:
    ----------
        @face_img: output face image with size (w, h) = @crop_size
    """

    if reference_pts is None:
        if crop_size[0] == 96 and crop_size[1] == 112:
            reference_pts = REFERENCE_FACIAL_POINTS
        else:
            default_square = False
            inner_padding_factor = 0
            outer_padding = (0, 0)
            output_size = crop_size

            reference_pts = get_reference_facial_points(output_size,
                                                        inner_padding_factor,
                                                        outer_padding,
                                                        default_square)

    ref_pts = np.float32(reference_pts)
    ref_pts_shp = ref_pts.shape
    if max(ref_pts_shp) < 3 or min(ref_pts_shp) != 2:
        raise FaceWarpException(
            'reference_pts.shape must be (K,2) or (2,K) and K>2')

    if ref_pts_shp[0] == 2:
        ref_pts = ref_pts.T

    src_pts = np.float32(facial_pts)
    src_pts_shp = src_pts.shape
    if max(src_pts_shp) < 3 or min(src_pts_shp) != 2:
        raise FaceWarpException(
            'facial_pts.shape must be (K,2) or (2,K) and K>2')

    if src_pts_shp[0] == 2:
        src_pts = src_pts.T

    if src_pts.shape != ref_pts.shape:
        raise FaceWarpException(
            'facial_pts and reference_pts must have the same shape')

    if align_type is 'cv2_affine':
        tfm = cv2.getAffineTransform(src_pts[0:3], ref_pts[0:3])
    elif align_type is 'affine':
        tfm = get_affine_transform_matrix(src_pts, ref_pts)
    else:
        tfm = get_similarity_transform_for_cv2(src_pts, ref_pts)

    face_img = cv2.warpAffine(src_img, tfm, (crop_size[0], crop_size[1]))

    return face_img


if __name__ == '__main__':
    print '\n=================================='
    print 'test get_reference_facial_points()'

    default_square = True
    inner_padding_factor = 0
    outer_padding = (0, 0)
    output_size = (112, 112)

    reference_5pts = get_reference_facial_points(output_size,
                                                 inner_padding_factor,
                                                 outer_padding,
                                                 default_square)

    print '--->reference_5pts:\n', reference_5pts

    try:
        import matplotlib.pyplot as plt
        dft_5pts = np.array(REFERENCE_FACIAL_POINTS)
        plt.title('Default 5 pts')
        plt.axis([0, 96, 112, 0])
        plt.scatter(dft_5pts[:, 0], dft_5pts[:, 1])

        plt.figure()
        plt.title('Transformed new 5 pts')
        plt.axis([0, 112, 112, 0])
        plt.scatter(reference_5pts[:, 0], reference_5pts[:, 1])
    except Exception as e:
        print 'Exception caught when trying to plot: ', e

    print '\n=================================='
    print 'test warp_and_crop_face()'

    img_fn = '../test_imgs/Jennifer_Aniston_0016.jpg'
    # imgSize = [96, 112]; # cropped dst image size

    # facial points in cropped dst image
    #    coord5points = [[30.2946, 65.5318, 48.0252, 33.5493, 62.7299],
    #                    [51.6963, 51.5014, 71.7366, 92.3655, 92.2041]];

    # facial points in src image
    # facial5points = [[105.8306, 147.9323, 121.3533, 106.1169, 144.3622],
    #                 [109.8005, 112.5533, 139.1172, 155.6359, 156.3451]];
    facial5points = [[105.8306,  109.8005],
                     [147.9323,  112.5533],
                     [121.3533,  139.1172],
                     [106.1169,  155.6359],
                     [144.3622,  156.3451]
                     ]

    print('Loading image {}'.format(img_fn))
    image = cv2.imread(img_fn, True)

    # swap BGR to RGB to show image by pyplot
    image_show = image[..., ::-1]

    plt.figure()
    plt.title('src image')
    plt.imshow(image_show)

    def crop_test(image,
                  facial5points,
                  reference_points=None,
                  output_size=(96, 112),
                  align_type='similarity'):

        dst_img = warp_and_crop_face(image,
                                     facial5points,
                                     reference_points,
                                     output_size,
                                     align_type)

        print 'warped image shape: ', dst_img.shape

        # swap BGR to RGB to show image by pyplot
        dst_img_show = dst_img[..., ::-1]

        plt.figure()
        plt.title(align_type + ' transform ' + str(output_size))
        plt.imshow(dst_img_show)

    print '===>test default crop setting with similarity transform'
    crop_test(image, facial5points)

    print '===>test default crop setting with cv2 affine transform'
    crop_test(image, facial5points, align_type='cv2_affine')

    print '===>test default crop setting with default affine transform'
    crop_test(image, facial5points, align_type='affine')

    print '===>test default square crop setting'
    # crop settings, set the region of cropped faces
    default_square = True
    inner_padding_factor = 0
    outer_padding = (0, 0)
    output_size = (112, 112)

    # get the reference 5 landmarks position in the crop settings
    reference_5pts = get_reference_facial_points(
        output_size, inner_padding_factor, outer_padding, default_square)
    print '--->reference_5pts:\n', reference_5pts

    print '===>test default square crop setting with similarity transform'
    crop_test(image, facial5points, reference_5pts, output_size)

    print '===>test default square crop setting with similarity transform'
    crop_test(image, facial5points, reference_5pts, output_size,
              align_type='cv2_affine')

    print '===>test default crop setting with default affine transform'
    crop_test(image, facial5points, reference_5pts, output_size,
              align_type='affine')